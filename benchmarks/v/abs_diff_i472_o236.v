module abs_diff_i472_o236(a,b,r);
input [235:0] a,b;
output [235:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
