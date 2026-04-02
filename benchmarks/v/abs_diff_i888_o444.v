module abs_diff_i888_o444(a,b,r);
input [443:0] a,b;
output [443:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
