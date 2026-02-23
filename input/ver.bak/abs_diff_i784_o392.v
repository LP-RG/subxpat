module abs_diff_i784_o392(a,b,r);
input [391:0] a,b;
output [391:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
