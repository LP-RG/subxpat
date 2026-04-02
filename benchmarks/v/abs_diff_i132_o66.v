module abs_diff_i132_o66(a,b,r);
input [65:0] a,b;
output [65:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
