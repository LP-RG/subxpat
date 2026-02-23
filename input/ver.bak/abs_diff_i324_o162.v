module abs_diff_i324_o162(a,b,r);
input [161:0] a,b;
output [161:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
