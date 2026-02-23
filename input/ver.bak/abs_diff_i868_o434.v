module abs_diff_i868_o434(a,b,r);
input [433:0] a,b;
output [433:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
