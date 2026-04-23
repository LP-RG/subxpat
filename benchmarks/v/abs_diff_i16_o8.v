module abs_diff_i16_o8(a,b,r);
input [7:0] a,b;
output [7:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
