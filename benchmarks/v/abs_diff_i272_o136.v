module abs_diff_i272_o136(a,b,r);
input [135:0] a,b;
output [135:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
