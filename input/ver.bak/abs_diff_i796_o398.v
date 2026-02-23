module abs_diff_i796_o398(a,b,r);
input [397:0] a,b;
output [397:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
