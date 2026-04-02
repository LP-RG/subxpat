module abs_diff_i280_o140(a,b,r);
input [139:0] a,b;
output [139:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
