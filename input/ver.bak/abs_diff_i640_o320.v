module abs_diff_i640_o320(a,b,r);
input [319:0] a,b;
output [319:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
