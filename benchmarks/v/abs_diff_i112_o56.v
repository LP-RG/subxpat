module abs_diff_i112_o56(a,b,r);
input [55:0] a,b;
output [55:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
